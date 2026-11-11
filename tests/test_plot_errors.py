#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A ``.plot()`` that raises leaves no figure behind.

A plot creates its figure first and draws into it after, so a keyword
matplotlib refuses (``colour="red"`` for ``color``) raised from the drawing
and left the half-drawn figure open: a notebook still showed it under the
traceback, and ``pyplot`` kept it until the kernel ended. The figure a plot
made is closed when the call raises; an axes the caller handed it is the
caller's, and stays.

Every result ``tests/result_factories.py`` builds is drawn here, so a new
result with a ``.plot()`` is held to it without a line of its own. The
``plot_*`` functions the domains publish, the plotting classes that are no
record and a filter bank that draws its response are drawn here too, each
from a small input of its own that a test holds to the published set.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import TYPE_CHECKING

import numpy as np
import pytest
import result_factories

import phonometry as ph
from phonometry._internal.display import RichDisplay
from phonometry._internal.figures import is_plotting_method

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

plt = pytest.importorskip("matplotlib.pyplot")


def _drawn() -> list[tuple[str, Callable[[], object]]]:
    """Every factory that builds a result unasked, by name."""
    found: list[tuple[str, Callable[[], object]]] = []
    for name, function in vars(result_factories).items():
        if not (
            inspect.isfunction(function)
            and function.__module__ == result_factories.__name__
            and name.startswith("_")
        ):
            continue
        parameters = inspect.signature(function).parameters.values()
        if any(p.default is p.empty and p.kind != p.VAR_KEYWORD for p in parameters):
            continue
        found.append((name, function))
    return found


def _plots(result: object) -> list[str]:
    """The names of the plotting methods of *result*: ``plot`` and ``plot_*``."""
    return sorted(
        name
        for name in dir(type(result))
        if is_plotting_method(name) and callable(getattr(result, name))
    )


@pytest.mark.parametrize(("name", "factory"), _drawn(), ids=[n for n, _ in _drawn()])
def test_a_plot_that_raises_closes_the_figure_it_made(
    name: str, factory: Callable[[], object]
) -> None:
    result = factory()
    methods = _plots(result)
    if not methods:
        pytest.skip(f"{name} builds a result with no plot")
    plt.close("all")
    left: list[str] = []
    for method in methods:
        try:
            getattr(result, method)(colour="red")
        except (AttributeError, TypeError, ValueError):
            if plt.get_fignums():
                left.append(method)
        plt.close("all")
    assert not left, f"{name}: {left} left a figure open after raising"


def test_a_plot_that_raises_leaves_the_caller_s_axes() -> None:
    """The axes the caller handed it, and its figure, are the caller's."""
    result = result_factories._airborne_rating()
    figure, ax = plt.subplots()
    try:
        with pytest.raises(AttributeError, match="colour"):
            result.plot(ax, colour="red")
        assert plt.fignum_exists(figure.number)
    finally:
        plt.close("all")


def _fdtd_with_an_obstacle() -> object:
    """A grid whose obstacle layer is drawn with the keywords the plot takes."""
    mask = np.zeros((8, 8), dtype=bool)
    mask[3:5, 3:5] = True
    return ph.simulation.FDTD2D(c=343.0, dx=0.01, shape=(8, 8), obstacle_mask=mask)


#: The plotting classes that are no record, so their methods are not wrapped
#: as the class is made: each wraps the renderer it hands the drawing to, and
#: is drawn here with a keyword matplotlib refuses, or that the method itself
#: refuses before any figure opens.
_NOT_RECORDS: dict[str, Callable[[], object]] = {
    "phonometry.noise_control.silencers.SilencerChain": lambda: (
        ph.noise_control.SilencerChain(np.array([100.0, 200.0])).duct(0.3, 0.04)
    ),
    "phonometry.simulation.fdtd.FDTD2D": _fdtd_with_an_obstacle,
}


def _plotting_classes_that_are_no_record() -> set[str]:
    """Every published class with a ``plot`` or ``plot_*`` that is no record."""
    found: set[str] = set()
    for info in pkgutil.walk_packages(ph.__path__, "phonometry."):
        if any(part.startswith("_") for part in info.name.split(".")[1:]):
            continue
        module = importlib.import_module(info.name)
        for name, obj in vars(module).items():
            if name.startswith("_") or not inspect.isclass(obj):
                continue
            if not obj.__module__.startswith("phonometry") or issubclass(
                obj, RichDisplay
            ):
                continue
            if any(is_plotting_method(member) for member in dir(obj)):
                found.add(f"{obj.__module__}.{obj.__qualname__}")
    return found


@pytest.mark.whole_tree
def test_every_plotting_class_that_is_no_record_is_drawn_here() -> None:
    assert _plotting_classes_that_are_no_record() == set(_NOT_RECORDS)


@pytest.mark.parametrize("owner", sorted(_NOT_RECORDS))
def test_a_plotting_class_that_is_no_record_closes_its_figure(owner: str) -> None:
    drawn = _NOT_RECORDS[owner]()
    plt.close("all")
    for method in _plots(drawn):
        draw = getattr(drawn, method)
        with pytest.raises((AttributeError, TypeError), match="colour"):
            draw(colour="red")
        assert not plt.get_fignums(), f"{owner}.{method} left a figure open"


def _resonator() -> ph.materials.HelmholtzResonator:
    return ph.materials.HelmholtzResonator(
        neck_length_m=0.002,
        neck_side_m=0.002,
        cavity_length_m=0.015,
        cavity_side_m=0.01,
    )


#: The sample rate of the excitation the room's ``plot_excitation`` draws.
_FS = 48000.0

#: Every ``plot_*`` function a public module publishes, by its domain, each
#: called on a small input of its own with the keywords the test passes.
_FUNCTIONS: dict[str, Callable[..., object]] = {
    "building.plot_aperture_geometry": lambda **kw: ph.building.plot_aperture_geometry(
        0.2, width_m=0.01, **kw
    ),
    "building.plot_double_wall_geometry": lambda **kw: (
        ph.building.plot_double_wall_geometry(10.0, 12.0, 0.1, **kw)
    ),
    "building.plot_facade_elements": lambda **kw: ph.building.plot_facade_elements(
        [ph.building.FacadeElement(name="Wall", area=6.0, r=[50.0] * 5)], **kw
    ),
    "building.plot_junction_geometry": lambda **kw: ph.building.plot_junction_geometry(
        "L", 0.14, 0.2, **kw
    ),
    "electroacoustics.plot_piston_geometry": lambda **kw: (
        ph.electroacoustics.plot_piston_geometry(0.1, **kw)
    ),
    "electroacoustics.plot_sound_reinforcement_geometry": lambda **kw: (
        ph.electroacoustics.plot_sound_reinforcement_geometry(1.0, 0.5, 10.0, **kw)
    ),
    "emission.plot_microphone_positions": lambda **kw: (
        ph.emission.plot_microphone_positions(
            ph.emission.measurement_positions("hemisphere", radius=2.0), **kw
        )
    ),
    "emission.plot_pp_probe_geometry": lambda **kw: ph.emission.plot_pp_probe_geometry(
        **kw
    ),
    "environment.plot_barrier_geometry": lambda **kw: (
        ph.environment.plot_barrier_geometry(
            source_height_m=1.0,
            barrier_distance=10.0,
            barrier_height_m=3.0,
            receiver_distance=20.0,
            receiver_height_m=1.5,
            **kw,
        )
    ),
    "materials.plot_absorber_stack": lambda **kw: ph.materials.plot_absorber_stack(
        [ph.materials.AirLayer(thickness_m=0.03)], **kw
    ),
    "materials.plot_dynamic_stiffness_rig": lambda **kw: (
        ph.materials.plot_dynamic_stiffness_rig(**kw)
    ),
    "materials.plot_goniometer_geometry": lambda **kw: (
        ph.materials.plot_goniometer_geometry(**kw)
    ),
    "materials.plot_helmholtz_resonator_geometry": lambda **kw: (
        ph.materials.plot_helmholtz_resonator_geometry(_resonator(), **kw)
    ),
    "materials.plot_impedance_tube_geometry": lambda **kw: (
        ph.materials.plot_impedance_tube_geometry(spacing_m=0.05, x1=0.15, **kw)
    ),
    "materials.plot_in_situ_geometry": lambda **kw: ph.materials.plot_in_situ_geometry(
        **kw
    ),
    "materials.plot_metadiffuser_panel_geometry": lambda **kw: (
        ph.materials.plot_metadiffuser_panel_geometry(
            [
                ph.materials.MetadiffuserWell(
                    slit_height_m=0.002, resonators=(_resonator(),)
                ),
                None,
            ],
            depth_m=0.03,
            period_m=0.02,
            **kw,
        )
    ),
    "materials.plot_qrd_geometry": lambda **kw: ph.materials.plot_qrd_geometry(
        [0.0, 0.05, 0.1], 0.1, **kw
    ),
    "materials.plot_slit_absorber_geometry": lambda **kw: (
        ph.materials.plot_slit_absorber_geometry(
            _resonator(),
            slit_height_m=0.002,
            lattice_step_m=0.015,
            period_m=0.02,
            **kw,
        )
    ),
    "materials.plot_transmission_tube_geometry": lambda **kw: (
        ph.materials.plot_transmission_tube_geometry(
            l1=0.1, s1=0.03, l2=0.15, s2=0.03, thickness_m=0.05, **kw
        )
    ),
    "noise_control.plot_plenum_geometry": lambda **kw: (
        ph.noise_control.plot_plenum_geometry(1.0, 2.0, 10.0, **kw)
    ),
    "noise_control.plot_silencer_geometry": lambda **kw: (
        ph.noise_control.plot_silencer_geometry(
            "expansion chamber",
            {"length": 0.3, "chamber_area": 0.1, "pipe_area": 0.01},
            **kw,
        )
    ),
    "room.plot_excitation": lambda **kw: ph.room.plot_excitation(
        ph.room.sweep_signal(_FS, 100.0, 4000.0, 0.1), _FS, **kw
    ),
    "room.plot_open_plan_geometry": lambda **kw: ph.room.plot_open_plan_geometry(
        [2.0, 4.0, 6.0], **kw
    ),
    "vibration.plot_plate_geometry": lambda **kw: ph.vibration.plot_plate_geometry(
        1.0, 2.0, **kw
    ),
}


def _published_plot_functions() -> dict[str, Callable[..., object]]:
    """Every ``plot_*`` function a public module publishes, by its domain.

    A function two modules publish is named after the first the walk meets.
    """
    found: dict[str, Callable[..., object]] = {}
    seen: set[int] = set()
    for info in pkgutil.walk_packages(ph.__path__, "phonometry."):
        if any(part.startswith("_") for part in info.name.split(".")[1:]):
            continue
        module = importlib.import_module(info.name)
        domain = info.name.split(".")[1]
        for name in getattr(module, "__all__", ()):
            obj = getattr(module, name, None)
            if name.startswith("plot_") and inspect.isfunction(obj):
                if id(obj) not in seen:
                    found[f"{domain}.{name}"] = obj
                seen.add(id(obj))
    return found


@pytest.mark.whole_tree
def test_every_published_plot_function_is_drawn_here() -> None:
    published = _published_plot_functions()
    assert set(published) == set(_FUNCTIONS)
    unmarked = sorted(
        name
        for name, function in published.items()
        if not getattr(function, "_closes_its_figures", False)
    )
    assert not unmarked, f"not wrapped with closes_its_figures: {unmarked}"


@pytest.mark.parametrize("name", sorted(_FUNCTIONS))
def test_a_published_plot_function_that_raises_closes_its_figure(name: str) -> None:
    draw = _FUNCTIONS[name]
    plt.close("all")
    with pytest.raises((AttributeError, TypeError), match="colour"):
        draw(colour="red")
    assert not plt.get_fignums(), f"{name} left a figure open"


def test_a_response_plot_that_cannot_be_saved_closes_its_figure(
    tmp_path: Path,
) -> None:
    """A filter bank that draws its response and fails to save it keeps no figure."""
    saved = ph.filters.ResponsePlot(file=str(tmp_path / "missing" / "response.png"))
    plt.close("all")
    with pytest.raises(FileNotFoundError, match="missing"):
        ph.filters.OctaveFilterBank(48000, response_plot=saved)
    assert not plt.get_fignums()

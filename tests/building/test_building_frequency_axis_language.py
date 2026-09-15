#  Copyright (c) 2026. Jose Manuel Requena Plens

"""The frequency labels of the building prediction figures follow the caller's language.

:func:`~phonometry._i18n.localize_axes` cannot reach tick labels installed as
fixed strings, so the octave labels of these figures are written by
``format_frequency_axis`` (or ``_format_freq`` for band categories) and by
nothing else: a renderer that does not pass its ``language`` on draws ``31.5``
in a Spanish figure. Every figure below spans 31,5 Hz, the lowest octave centre
whose label carries a decimal, because a label without one proves nothing.

The marker entries (``fco``, ``fo``) are mathtext, which the save-time comma
pass of the figure pipeline skips, so their value has to arrive localised too.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

import phonometry as ph

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from matplotlib.axes import Axes

_THIRDS = np.array(
    [
        25.0,
        31.5,
        40.0,
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
    ]
)
_OCTAVES = [31.5, 63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0]


@pytest.fixture(autouse=True)
def _close_figures() -> Iterator[None]:
    yield
    plt.close("all")


def _tick_labels(ax: Axes) -> list[str]:
    return [t.get_text() for t in ax.get_xticklabels() if t.get_text()]


def _concrete_slab() -> tuple[float, float]:
    """Contact stiffness and point impedance of a 140 mm concrete slab."""
    density, velocity, poisson, thickness = 2200.0, 3800.0, 0.2, 0.14
    modulus = density * velocity**2 * (1 - poisson**2)
    impedance = ph.vibration.infinite_plate_impedance(
        ph.vibration.plate_bending_stiffness(modulus, thickness, poisson),
        density * thickness,
    )
    stiffness = ph.building.plate_contact_stiffness(modulus, poisson_ratio=poisson)
    return stiffness, impedance


def _sound_reduction(language: str) -> Axes:
    result = ph.building.single_panel_transmission_loss(
        _THIRDS, 15.0, critical_frequency=1000.0, loss_factor=0.024
    )
    return result.plot(language=language)


def _aperture(language: str) -> Axes:
    result = ph.building.slit_transmission_coefficient(_THIRDS, 0.002, 0.1)
    return result.plot(language=language)


def _radiated_power(language: str) -> Axes:
    result = ph.building.radiated_sound_power(
        [
            ph.building.FacadeElement(
                "wall", area=176.0, r=[36, 36, 33, 39, 49, 57, 63]
            ),
            ph.building.FacadeElement(
                "door", area=24.0, r=[23, 28, 30, 30, 30, 30, 30]
            ),
        ],
        lp_in=[74, 76, 72, 70, 67, 62, 57],
        area=200.0,
        c_d=-5.0,
        octave_bands=[63, 125, 250, 500, 1000, 2000, 4000],
    )
    # EN 12354-4 works in the octaves from 63 Hz, and none of their labels
    # carries a decimal, so the band centres are moved one octave down to reach
    # 31,5 Hz; the levels drawn over them are left as computed.
    shifted = dataclasses.replace(result, frequencies=np.array(_OCTAVES[:-1]))
    return shifted.plot(language=language)


def _installed_structure_borne(language: str) -> Axes:
    n = len(_OCTAVES)
    result = ph.building.installed_source_prediction(
        [60.0] * n,
        [5.0] * n,
        [
            {
                "adjustment_term": [20.0] * n,
                "flanking_reduction_index": [50.0] * n,
                "element_area": 10.0,
            }
        ],
        frequencies=_OCTAVES,
    )
    return result.plot(language=language)


def _in_situ_element(language: str) -> Axes:
    element = ph.building.HomogeneousElement(
        label="floor",
        area=20.0,
        length1=5.0,
        length2=4.0,
        mass_per_area=400.0,
        critical_frequency=100.0,
    )
    return ph.building.in_situ_element(element, _THIRDS[1:]).plot(language=language)


def _wall_tie_coupling(language: str) -> Axes:
    result = ph.building.wall_tie_coupling_loss_factor(
        _THIRDS, 150.0, 170.0, 1.0e5, 1.2e5, ties_per_area=2.5, tie="butterfly"
    )
    return result.plot(language=language)


def _tapping_force(language: str) -> Axes:
    stiffness, impedance = _concrete_slab()
    result = ph.building.tapping_force_spectrum(_THIRDS, stiffness, impedance)
    return result.plot(language=language)


def _covering_improvement(language: str) -> Axes:
    plate_stiffness, impedance = _concrete_slab()
    thickness = 0.005
    covering = ph.building.covering_contact_stiffness(2.8e8 * thickness, thickness)
    result = ph.building.covering_improvement(
        _THIRDS, covering, plate_stiffness, impedance
    )
    return result.plot(language=language)


def _floating_floor_improvement(language: str) -> Axes:
    result = ph.building.floating_floor_improvement_spectrum(
        _THIRDS, resonance_frequency=52.8
    )
    return result.plot(language=language)


def _lining_improvement(language: str) -> Axes:
    return ph.building.lining_improvement(87.5).plot(language=language)


_FIGURES = [
    pytest.param(_sound_reduction, id="sound-reduction"),
    pytest.param(_aperture, id="aperture-transmission"),
    pytest.param(_radiated_power, id="radiated-power"),
    pytest.param(_installed_structure_borne, id="installed-structure-borne"),
    pytest.param(_in_situ_element, id="in-situ-element"),
    pytest.param(_wall_tie_coupling, id="wall-tie-coupling"),
    pytest.param(_tapping_force, id="tapping-force"),
    pytest.param(_covering_improvement, id="covering-improvement"),
    pytest.param(_floating_floor_improvement, id="floating-floor-improvement"),
    pytest.param(_lining_improvement, id="lining-improvement"),
]


@pytest.mark.parametrize("draw", _FIGURES)
def test_the_frequency_labels_reach_spanish(draw: Callable[[str], Axes]) -> None:
    labels = _tick_labels(draw("es"))
    assert any("," in label for label in labels), labels
    assert all("." not in label for label in labels), labels


@pytest.mark.parametrize("draw", _FIGURES)
def test_the_frequency_labels_are_unchanged_in_english(
    draw: Callable[[str], Axes],
) -> None:
    labels = _tick_labels(draw("en"))
    assert any("." in label for label in labels), labels
    assert all("," not in label for label in labels), labels


def _marker_value(ax: Axes, symbol: str) -> str:
    """The value half of the one legend entry that marks ``symbol``."""
    legend = ax.get_legend()
    assert legend is not None
    (entry,) = [
        text.get_text()
        for text in legend.get_texts()
        if text.get_text().startswith(f"{symbol} = ")
    ]
    return entry.removeprefix(f"{symbol} = ")


_MARKERS = [
    pytest.param(_tapping_force, r"$f_\mathrm{co}$", id="tapping-force"),
    pytest.param(_covering_improvement, r"$f_\mathrm{co}$", id="covering-improvement"),
    pytest.param(
        _floating_floor_improvement, r"$f_\mathrm{o}$", id="floating-floor-improvement"
    ),
    pytest.param(_lining_improvement, r"$f_\mathrm{o}$", id="lining-improvement"),
]


@pytest.mark.parametrize(("draw", "symbol"), _MARKERS)
def test_the_marked_frequency_reaches_spanish(
    draw: Callable[[str], Axes], symbol: str
) -> None:
    value = _marker_value(draw("es"), symbol)
    assert "," in value, value
    assert "." not in value, value


@pytest.mark.parametrize(("draw", "symbol"), _MARKERS)
def test_the_marked_frequency_is_unchanged_in_english(
    draw: Callable[[str], Axes], symbol: str
) -> None:
    value = _marker_value(draw("en"), symbol)
    assert "." in value, value
    assert "," not in value, value

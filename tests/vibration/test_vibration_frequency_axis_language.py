#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The frequency ticks of the vibration renderers reach Spanish.

``localize_axes`` cannot reach tick labels installed as fixed strings, so the
band-centre labels of a continuous frequency axis are written by
``format_frequency_axis`` and by nothing else: a renderer that does not hand
its ``language`` down draws 31.5 on a Spanish figure where 31,5 belongs. Every
range here reaches down past 31,5 Hz, the lowest octave centre whose label
carries a decimal, because a set of labels without one proves nothing.

The rigid-mass calibration check formats the axis from two places, once for
the deviation panel drawn on the caller's axes and once per panel of its own
figure, so both paths are drawn.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

import numpy as np
import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt

from phonometry import vibration

if TYPE_CHECKING:
    from collections.abc import Callable

    from matplotlib.axes import Axes
    from numpy.typing import NDArray

    from phonometry.vibration.human.exposure import WeightingResponse
    from phonometry.vibration.structural.experimental_sea import PowerInjectionResult
    from phonometry.vibration.structural.mechanical_mobility import (
        MobilityResult,
        RigidMassCalibrationResult,
    )
    from phonometry.vibration.structural.radiation_efficiency import (
        RadiationEfficiencyResult,
    )
    from phonometry.vibration.structural.transfer_stiffness import (
        BandAveragedStiffness,
        DrivingPointStiffnessResult,
        EffectiveBlockingMass,
        LevelDifferenceCheck,
        OutputMassCheck,
        TransferStiffnessResult,
    )

    Drawn = Axes | NDArray[Any]


class _Plottable(Protocol):
    def plot(self, ax: Axes | None = None, *, language: str = "en") -> Drawn: ...


def _weighting() -> WeightingResponse:
    return vibration.frequency_weighting("Wk", np.geomspace(1.0, 100.0, 60))


def _mobility() -> MobilityResult:
    return vibration.sdof_mobility_result(
        np.geomspace(10.0, 500.0, 200), 2.0, 8000.0, 5.0
    )


def _rigid_mass_calibration() -> RigidMassCalibrationResult:
    return vibration.rigid_mass_calibration_check(
        [0.100, 0.102, 0.101, 0.097], [20.0, 50.0, 100.0, 500.0], mass=10.0
    )


def _transfer_stiffness() -> TransferStiffnessResult:
    f = np.array([25.0, 50.0, 100.0, 200.0, 400.0])
    t = np.array([0.08, 0.05, 0.02, 0.008, 0.004]) * np.exp(1j * 0.1)
    return vibration.indirect_transfer_stiffness_result(f, t, blocking_mass=8.0)


def _blocked_output() -> LevelDifferenceCheck:
    return vibration.check_blocked_output(
        [20.0, 31.5, 63.0, 125.0], [100.0] * 4, [70.0, 72.0, 75.0, 78.0]
    )


def _output_mass() -> OutputMassCheck:
    return vibration.check_output_mass(
        [20.0, 31.5, 63.0, 125.0], 0.1, [120.0] * 4, [100.0, 102.0, 104.0, 106.0]
    )


def _effective_blocking_mass() -> EffectiveBlockingMass:
    f = np.geomspace(20.0, 5000.0, 100)
    ones = np.ones(f.size, dtype=complex)
    m_eff = 20.0 * (1.0 + (f / 3000.0) ** 2)
    return vibration.effective_blocking_mass(
        f, m_eff * ones, ones, ones, blocking_mass_kg=20.0
    )


def _driving_point() -> DrivingPointStiffnessResult:
    f = np.arange(1.0, 200.0, 0.2)
    w = 2.0 * np.pi * f
    return vibration.driving_point_stiffness(
        f, (1.0e6 - 2.0 * w**2) * 1.0e-6, -(w**2) * 1.0e-6
    )


def _band_average() -> BandAveragedStiffness:
    """Lines every hertz from 18 Hz: five or more in every band from 20 Hz up."""
    f = np.arange(18.0, 500.0, 1.0)
    return vibration.band_averaged_stiffness(f, np.full(f.size, 1.0e6 + 0j))


def _radiation_efficiency() -> RadiationEfficiencyResult:
    # 6 mm glass on a 1,5 m by 1,25 m pane.
    bending_stiffness = vibration.plate_bending_stiffness(6.2e10, 0.006, 0.24)
    critical = vibration.coincidence_frequency(2500.0 * 0.006, bending_stiffness)
    return vibration.radiation_efficiency(
        np.geomspace(20.0, 5000.0, 60), 1.5, 1.25, critical
    )


def _power_injection() -> PowerInjectionResult:
    """Energies of a forward two-subsystem SEA model, inverted back."""
    f = np.array([31.5, 63.0, 125.0, 250.0, 500.0, 1000.0])
    eta_1, eta_2, eta_12, n_1, n_2 = 1.0e-2, 1.0e-2, 1.0e-3, 2.0, 2.0
    eta_21 = eta_12 * n_1 / n_2
    ratio = eta_12 / (eta_2 + eta_21)
    e_1 = 1.0 / (2.0 * np.pi * f * ((eta_1 + eta_12) - ratio * eta_21))
    return vibration.power_injection_clf(f, e_1, ratio * e_1, eta_1, eta_2, n_1, n_2)


def _own_figure(build: Callable[[], _Plottable]) -> Callable[[str], Drawn]:
    return lambda language: build().plot(language=language)


def _on_axes(build: Callable[[], _Plottable]) -> Callable[[str], Drawn]:
    def draw(language: str) -> Drawn:
        _fig, ax = plt.subplots()
        return build().plot(ax=ax, language=language)

    return draw


_CASES = [
    pytest.param(_own_figure(_weighting), id="vibration_weighting"),
    pytest.param(_own_figure(_mobility), id="mobility"),
    pytest.param(_own_figure(_rigid_mass_calibration), id="rigid_mass_calibration"),
    pytest.param(
        _on_axes(_rigid_mass_calibration), id="rigid_mass_calibration-on-axes"
    ),
    pytest.param(_own_figure(_transfer_stiffness), id="transfer_stiffness"),
    pytest.param(_own_figure(_blocked_output), id="blocked_output"),
    pytest.param(_own_figure(_output_mass), id="output_mass"),
    pytest.param(_own_figure(_effective_blocking_mass), id="effective_blocking_mass"),
    pytest.param(_own_figure(_driving_point), id="driving_point_stiffness"),
    pytest.param(_own_figure(_band_average), id="band_averaged_stiffness"),
    pytest.param(_own_figure(_radiation_efficiency), id="radiation_efficiency"),
    pytest.param(_own_figure(_power_injection), id="power_injection"),
]


def _frequency_tick_labels(drawn: Drawn) -> list[str]:
    """Every non-empty x tick label of the panels a renderer returned.

    A column of panels shares one frequency axis and only the bottom panel
    shows its labels, so the panels are read together.
    """
    axes = drawn.ravel() if isinstance(drawn, np.ndarray) else [drawn]
    return [t.get_text() for ax in axes for t in ax.get_xticklabels() if t.get_text()]


@pytest.mark.parametrize("draw", _CASES)
def test_the_frequency_ticks_reach_spanish(draw: Callable[[str], Drawn]) -> None:
    labels = _frequency_tick_labels(draw("es"))
    plt.close("all")
    assert "31,5" in labels, labels
    assert all("." not in label for label in labels), labels


@pytest.mark.parametrize("draw", _CASES)
def test_the_frequency_ticks_are_unchanged_in_english(
    draw: Callable[[str], Drawn],
) -> None:
    labels = _frequency_tick_labels(draw("en"))
    plt.close("all")
    assert "31.5" in labels, labels


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        ("es", "Frecuencia de tercio de octava [Hz]"),
        ("en", "One-third-octave frequency [Hz]"),
    ],
)
def test_the_band_axis_is_named_in_the_figure_language(
    language: str, expected: str
) -> None:
    """The band axis label reaches Spanish, not only its ticks.

    The label is handed to the shared band-axis helper, which looks strings
    up in its own table only; one it does not carry came back in English on
    a figure whose title, legend and y label were Spanish.
    """
    ax = _band_average().plot(language=language)
    label = ax.get_xlabel()
    plt.close("all")
    assert label == expected

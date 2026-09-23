#  Copyright (c) 2026. Jose Manuel Requena Plens

"""The frequency labels of the materials figures follow the caller's language.

:func:`~phonometry._i18n.localize_axes` cannot reach tick labels installed as
fixed strings, so the octave labels of these figures are written by
``format_frequency_axis`` and by nothing else: a renderer that does not pass
its ``language`` on draws ``31.5`` in a Spanish figure. Every figure below
spans 31,5 Hz, the lowest octave centre whose label carries a decimal, because
a label without one proves nothing.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry import materials
from phonometry.materials.absorbers.four_microphone import TransferMatrix
from phonometry.materials.absorbers.impedance_tube import ImpedanceTubeResult
from phonometry.materials.absorbers.layered import (
    PorousLayer,
    diffuse_field_absorption,
)
from phonometry.materials.absorbers.porous import PUBLISHED_AIR, delany_bazley

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from matplotlib.axes import Axes

#: 20 Hz to 2 kHz: seven octave labels, the first of them 31,5.
_FREQUENCIES = np.geomspace(20.0, 2000.0, 30)

#: Characteristic impedance of air, rho c, in rayls.
_RHO_C = 1.205 * 343.0


@pytest.fixture(autouse=True)
def _close_figures() -> Iterator[None]:
    yield
    plt.close("all")


def _tick_labels(ax: Axes) -> list[str]:
    return [t.get_text() for t in ax.get_xticklabels() if t.get_text()]


def _medium() -> materials.PorousMediumResult:
    # Delany-Bazley is fitted above 250 Hz; its range warning is not the
    # subject here, only the axis the result is drawn on.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return delany_bazley(_FREQUENCIES, 20000.0, fluid=PUBLISHED_AIR)


def _impedance_tube(language: str) -> Axes:
    reflection = np.full(_FREQUENCIES.shape, 0.4 - 0.3j)
    normalized = (1.0 + reflection) / (1.0 - reflection)
    result = ImpedanceTubeResult(
        frequencies=_FREQUENCIES,
        reflection=reflection,
        surface_impedance=_RHO_C * normalized,
        normalized_impedance=normalized,
        absorption=1.0 - np.abs(reflection) ** 2,
    )
    return result.plot(language=language)


def _porous_medium(language: str) -> Axes:
    return _medium().plot(language=language)


def _diffuse_field(language: str) -> Axes:
    # Drawn through the shared absorption-spectrum axes of the materials module.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = diffuse_field_absorption(_FREQUENCIES, [PorousLayer(0.05, _medium())])
    return result.plot(language=language)


def _biot_waves(language: str) -> Axes:
    glass_wool = materials.PUBLISHED_POROUS["allard-2009-table-6-1/domisol_coffrage"]
    shear, poisson = glass_wool.frame_constants()
    result = materials.biot_waves(
        glass_wool.medium(_FREQUENCIES),
        porosity=glass_wool.porosity,
        tortuosity=glass_wool.tortuosity,
        frame_density=glass_wool.frame_density_kg_m3,
        shear_modulus=shear,
        poisson_ratio=poisson,
    )
    return result.plot(language=language)


def _transfer_matrix(language: str) -> Axes:
    # A limp 0.5 kg/m² mass layer: T12 = j omega m, the rest of the identity.
    ones = np.ones(_FREQUENCIES.shape, dtype=np.complex128)
    matrix = TransferMatrix(
        t11=ones,
        t12=1j * 2.0 * np.pi * _FREQUENCIES * 0.5,
        t21=np.zeros_like(ones),
        t22=ones,
    )
    return matrix.plot(
        frequencies=_FREQUENCIES, characteristic_impedance=_RHO_C, language=language
    )


_FIGURES: list[Callable[[str], Axes]] = [
    _impedance_tube,
    _porous_medium,
    _diffuse_field,
    _biot_waves,
    _transfer_matrix,
]


@pytest.mark.parametrize("draw", _FIGURES, ids=lambda draw: draw.__name__[1:])
def test_the_frequency_labels_reach_spanish(draw: Callable[[str], Axes]) -> None:
    labels = _tick_labels(draw("es"))
    assert "31,5" in labels, labels
    assert all("." not in label for label in labels), labels


@pytest.mark.parametrize("draw", _FIGURES, ids=lambda draw: draw.__name__[1:])
def test_the_frequency_labels_are_unchanged_in_english(
    draw: Callable[[str], Axes],
) -> None:
    labels = _tick_labels(draw("en"))
    assert "31.5" in labels, labels
    assert all("," not in label for label in labels), labels

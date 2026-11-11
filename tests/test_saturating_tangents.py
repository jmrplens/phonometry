#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A complex tangent that saturates warns on no platform.

``tanh(z)`` tends to ``±1`` as the real part of ``z`` grows, and ``tan(z)``
to ``±i`` as its imaginary part does. NumPy on Linux and macOS computes both
through the C library and returns the limit without a word; NumPy on
Windows computes them through its own routines, which pass through an
exponential that overflows once the growing part passes about 354, and
says "overflow encountered in tanh" (or ``tan``) from the library's line,
an error under ``python -W error``. The Windows test cells listed three such
lines: the layered absorber's tangent, the slit's two boundary-layer
functions, and the coupler's heat-conduction sum. The same tangent of an
argument that grows with an input the function accepts sits in three more
places: Maekawa's barrier ratio with the Fresnel number, the Biot layer's
impedance with its thickness, and the capillary tube's impedance with its
length. Each saturates in an ``np.errstate(over="ignore")`` block now.

Each case runs twice, on inputs whose growing part passes the threshold:
with NumPy's own functions, which is what Windows checks, and with
functions that overflow as Windows' do, which shows on every platform
whether the call sits in such a block.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import numpy as np
import pytest

import phonometry as ph
from phonometry.materials.absorbers.porous import ABSORBER_AIR
from phonometry.materials.absorbers.slow_sound import slit_effective_properties

if TYPE_CHECKING:
    from collections.abc import Callable

#: Where Windows' exponential overflows: exp(2 * 354.9) is past the largest
#: float64.
_WINDOWS_LIMIT = 354.0


def _layered_absorber() -> object:
    frequency = np.geomspace(100.0, 1000.0, 50)
    with pytest.warns(ph.materials.PorousAbsorberWarning):
        medium = ph.materials.miki(frequency, 1e9, fluid=ABSORBER_AIR)
    return ph.materials.layered_absorber(
        frequency, [ph.materials.PorousLayer(thickness_m=0.05, medium=medium)]
    )


def _slit() -> object:
    return slit_effective_properties(
        np.array([2.0e4]), slit_height_m=5.0e-2, fluid=ABSORBER_AIR
    )


def _heat_conduction() -> object:
    return ph.metrology.temperature_transfer_function(1.0, 4000.0)


def _barrier() -> object:
    return ph.environment.kurze_anderson_attenuation(np.array([1.0e3, 1.0e6]))


def _biot_layer() -> object:
    glass_wool = ph.materials.PUBLISHED_POROUS_MATERIALS[
        "allard-2009-table-6-1/domisol_coffrage"
    ]
    frequency = np.array([1000.0, 4000.0])
    frame = glass_wool.frame_constants()
    waves = ph.materials.biot_waves(
        glass_wool.medium(frequency),
        porosity=glass_wool.porosity,
        tortuosity=glass_wool.tortuosity,
        frame_density=glass_wool.frame_density_kg_m3,
        shear_modulus=frame.shear_modulus_pa,
        poisson_ratio=frame.poisson_ratio,
    )
    return ph.materials.biot_surface_impedance(waves, 20.0)


def _capillary() -> object:
    tube = ph.metrology.capillary_tube_impedance(
        [2000.0],
        length_m=100.0,
        radius_m=1.0 / 6000.0,
        gas=ph.fluids.air(
            temperature_c=23.0,
            static_pressure_pa=101325.0,
            relative_humidity_percent=50.0,
        ),
    )
    return tube.impedance_pa_s_m3


#: Each call, by the line whose tangent it saturates.
_SATURATING: dict[str, Callable[[], object]] = {
    "materials/absorbers/layered.py: tan(k_x d)": _layered_absorber,
    "materials/absorbers/slow_sound.py: tanh of the slit's boundary layers": _slit,
    "metrology/reciprocity_coupler.py: tanh in the heat-conduction sum": (
        _heat_conduction
    ),
    "environment/propagation/ground_barriers.py: x / tanh(x)": _barrier,
    "materials/absorbers/biot.py: tan(delta d)": _biot_layer,
    "metrology/reciprocity_coupler.py: tanh(gamma l)": _capillary,
}


def _overflowing_as_windows_does(
    name: str, monkeypatch: pytest.MonkeyPatch, reached: list[float]
) -> None:
    """Replace ``np.tan`` and ``np.tanh`` with ones that overflow as Windows' do.

    Each returns NumPy's value, after the exponential Windows' routine
    passes through, which overflows past :data:`_WINDOWS_LIMIT` and warns
    unless the caller ignores overflow.
    """
    exact = getattr(np, name)

    def windows(z: object, *args: object, **kwargs: object) -> object:
        values = np.asarray(z)
        if np.iscomplexobj(values) and values.size:
            growing = values.imag if name == "tan" else values.real
            largest = float(np.nanmax(np.abs(growing), initial=0.0))
            reached.append(largest)
            np.exp(2.0 * np.minimum(largest, 1.0e4))
        return exact(z, *args, **kwargs)

    monkeypatch.setattr(np, name, windows)


@pytest.mark.parametrize("site", sorted(_SATURATING))
def test_a_saturating_tangent_says_nothing_with_numpy_s_own_functions(
    site: str,
) -> None:
    """What Windows checks: NumPy's own tangents raise no warning under ``-W error``."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        warnings.filterwarnings("ignore", category=ph.PhonometryWarning)
        _SATURATING[site]()


@pytest.mark.parametrize("site", sorted(_SATURATING))
def test_a_saturating_tangent_is_computed_where_overflow_is_ignored(
    site: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    reached: list[float] = []
    for name in ("tan", "tanh"):
        _overflowing_as_windows_does(name, monkeypatch, reached)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        warnings.filterwarnings("ignore", category=ph.PhonometryWarning)
        _SATURATING[site]()
    assert max(reached) > _WINDOWS_LIMIT, f"{site}: the input does not overflow"

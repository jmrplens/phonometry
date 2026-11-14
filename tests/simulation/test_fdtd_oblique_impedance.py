#  Copyright (c) 2026. Jose Manuel Requena Plens
"""An impedance edge of the acoustic FDTD engine reflects as a locally reacting plane.

The edge update of Attenborough & Van Renterghem (2021), Eqs. 4.33-4.35,
ties the pressure on the wall face to the normal velocity there,
``p = Z v_n`` (Eq. 4.34), whatever the direction the wave arrives from. That
is the definition of a locally reacting plane, whose plane-wave reflection
coefficient at an angle ``theta`` from the normal is
``R = (Z cos(theta) - rho c) / (Z cos(theta) + rho c)``, the real-impedance
case of the oblique absorption of Mechel (2008), Sect. D.5, Eq. (6):
``alpha = 4 z cos(theta) / (1 + z cos(theta))^2`` with ``z = Z / (rho c)``.

The other tests of the edge are at normal incidence and in ducts. Here a
point source stands half a metre above the edge and receivers at the same
height read the reflection at specular angles from 20 to 80 degrees. Three
runs separate it: the edge at ``Z``, the same edge rigid (a perfect mirror
at every angle) and no edge at all. The reflected pulse over the rigid one
is ``R(theta)``, the spreading and the dispersion of the grid being the same
in both.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np
import pytest

from phonometry.simulation import FDTD2D, GaussianPulse

if TYPE_CHECKING:
    from numpy.typing import NDArray

C, RHO, DX = 343.0, 1.2, 0.02
#: The impedance of a normal-incidence absorption of 0.9, in units of rho c.
Z_NORMALIZED = (1.0 + np.sqrt(0.1)) / (1.0 - np.sqrt(0.1))
HEIGHT_M = 0.5
ANGLES_DEG = (20.0, 40.0, 58.7, 70.0, 80.0)
SPONGE = 25
HALF_WIDTH_S = 1.6e-4


def _traces(
    kind: Literal["impedance", "rigid", "free"],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """The pressure at the receivers, and their specular angles [deg].

    :param kind: What closes the bottom of the domain: the impedance edge,
        a rigid edge, or nothing (the domain runs on into a sponge).
    """
    offsets = 2.0 * HEIGHT_M * np.tan(np.radians(ANGLES_DEG))
    lead = round(0.5 / DX)
    nx = SPONGE + lead + round(float(offsets.max()) / DX) + lead + SPONGE
    rows = round(2.0 / DX)
    free = kind == "free"
    ny = SPONGE + rows + (round(2.5 / DX) + SPONGE if free else 0)
    sim = FDTD2D(
        c=C,
        dx=DX,
        rho=RHO,
        shape=(ny, nx),
        absorbing_layer_cells=SPONGE,
        absorbing_sides=("left", "right", "top", "bottom")
        if free
        else ("left", "right", "top"),
        edge_impedance={"bottom": Z_NORMALIZED * RHO * C}
        if kind == "impedance"
        else None,
    )
    wall = SPONGE + rows  # the wall face is the lower side of row ``wall - 1``
    iy = wall - round(HEIGHT_M / DX)
    ix = SPONGE + lead
    sim.add_source(GaussianPulse(ix=ix, iy=iy, half_width_s=HALF_WIDTH_S))
    cols = [ix + round(float(offset) / DX) for offset in offsets]
    longest = float(np.hypot(offsets.max(), 2.0 * HEIGHT_M))
    steps = round((longest / C + 12.0 * HALF_WIDTH_S) / sim.dt)
    record = np.zeros((steps, len(cols)))
    for step in range(steps):
        sim.step()
        record[step] = sim.numpy_field("p")[iy, cols]
    height = (wall - iy - 0.5) * DX
    angles = np.degrees(np.arctan2((np.asarray(cols) - ix) * DX, 2.0 * height))
    return record, angles


def test_impedance_edge_reflects_obliquely_as_a_locally_reacting_plane() -> None:
    with_edge, angles = _traces("impedance")
    rigid, _ = _traces("rigid")
    free, _ = _traces("free")
    reflected = with_edge - free
    mirrored = rigid - free
    measured = np.sum(reflected * mirrored, axis=0) / np.sum(mirrored**2, axis=0)
    cosines = np.cos(np.radians(angles))
    expected = (Z_NORMALIZED * cosines - 1.0) / (Z_NORMALIZED * cosines + 1.0)
    assert measured == pytest.approx(expected, abs=0.02)
    # The reflection changes sign where cos(theta) = rho c / Z, 58.7 degrees
    # here: positive inside it, negative beyond, so the absorption
    # 1 - R^2 rises with the angle up to there and is above its value at
    # normal incidence, 0.9, at every angle read short of 74.3 degrees.
    assert measured[0] > 0.2
    assert measured[-1] < -0.4
    assert abs(measured[2]) < 0.02
    absorption = 1.0 - measured**2
    assert np.all(absorption[:4] > 0.9)

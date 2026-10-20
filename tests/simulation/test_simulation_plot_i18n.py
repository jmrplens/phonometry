#  Copyright (c) 2026. Jose Manuel Requena Plens

"""The simulation (FDTD) ``.plot()`` renderer: its EN/ES labels, and its decimated snapshots."""

from __future__ import annotations

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry.simulation import (
    ElasticRecording,
    ExplosionSource,
    elastic_fdtd_simulation,
)
from phonometry.simulation.fdtd import GaussianPulse, fdtd_simulation


def _result() -> object:
    mask = np.zeros((30, 40), dtype=bool)
    mask[12:18, 20:22] = True
    return fdtd_simulation(
        343.0,
        9.0e-3,
        3.0e-3,
        shape=(30, 40),
        sources=[GaussianPulse(ix=7, iy=5, half_width_s=3.0e-4)],
        probes=[(10, 5), (24, 10)],
        obstacle_mask=mask,
        snapshot_every=10,
    )


def test_fdtd_probes_es_and_bad_language() -> None:
    res = _result()
    ax = res.plot(kind="probes", language="es")
    assert ax.get_title() == "Presión en las sondas FDTD"
    assert ax.get_ylabel() == "Presión [Pa]"
    assert ax.get_xlabel() == "Tiempo [ms]"
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert any(s.startswith("sonda") for s in labels)
    plt.close("all")
    with pytest.raises(ValueError, match="Unknown language"):
        res.plot(language="xx")


def test_fdtd_snapshot_es() -> None:
    res = _result()
    ax = res.plot(kind="snapshot", frame=-1, language="es")
    assert ax.get_title().startswith("Campo de presión FDTD en $t$ =")
    plt.close("all")
    with pytest.raises(ValueError, match="Unknown language"):
        res.plot(kind="snapshot", language="xx")


def test_a_decimated_snapshot_covers_the_domain_without_stretching() -> None:
    res = fdtd_simulation(
        343.0,
        0.01,
        1e-3,
        shape=(30, 101),
        sources=[GaussianPulse(ix=50, iy=15, half_width_s=4e-5)],
        snapshot_every=10,
        snapshot_decimation=4,
    )
    ax = res.plot(kind="snapshot")
    image = ax.images[0]
    left, right, bottom, top = image.get_extent()
    assert (left, top) == (0.0, 0.0)
    assert right == pytest.approx(26 * 4 * 0.01)
    assert bottom == pytest.approx(8 * 4 * 0.01)
    assert ax.get_xlim() == pytest.approx((0.0, 1.01))
    assert ax.get_ylim() == pytest.approx((0.30, 0.0))
    plt.close(ax.figure)


def test_the_obstacles_of_a_decimated_snapshot_stay_on_the_domain() -> None:
    # The obstacle map is the full grid whatever the snapshots keep, so it is
    # drawn over the domain, not over the blocks of the decimated field.
    mask = np.zeros((30, 101), dtype=bool)
    mask[10:20, 60:70] = True
    res = fdtd_simulation(
        343.0,
        0.01,
        1e-3,
        shape=(30, 101),
        sources=[GaussianPulse(ix=50, iy=15, half_width_s=4e-5)],
        obstacle_mask=mask,
        snapshot_every=10,
        snapshot_decimation=4,
    )
    ax = res.plot(kind="snapshot")
    assert ax.images[1].get_extent() == pytest.approx([0.0, 1.01, 0.30, 0.0])
    plt.close(ax.figure)


def test_a_decimated_elastic_snapshot_covers_the_domain_without_stretching() -> None:
    def pulse(t: float) -> float:
        return float(np.exp(-(((t - 2e-5) / 5e-6) ** 2)))

    res = elastic_fdtd_simulation(
        4000.0,
        2300.0,
        0.01,
        1e-4,
        rho=2500.0,
        shape=(20, 21),
        sources=[ExplosionSource(ix=10, iy=9, waveform=pulse)],
        recording=ElasticRecording(snapshot_every=4, snapshot_decimation=3),
    )
    ax = res.plot(kind="snapshot")
    # ceil(20 / 3) rows and ceil(21 / 3) columns of 3-cell blocks: the last
    # row of blocks overhangs the 20-cell domain by one cell, cut at the edge.
    assert ax.images[0].get_extent() == pytest.approx([0.0, 0.21, 0.21, 0.0])
    assert ax.get_xlim() == pytest.approx((0.0, 0.21))
    assert ax.get_ylim() == pytest.approx((0.20, 0.0))
    plt.close(ax.figure)


def test_an_undecimated_snapshot_is_drawn_as_it_was() -> None:
    """With every cell kept, the field and its obstacles span the domain.

    The limits are the ones the two images set (0 to 0.36 m across, 0.27 m
    to 0 down, as before snapshots could be decimated), and neither axis is
    pinned by hand: autoscaling is still on, which a call to ``set_xlim`` or
    ``set_ylim`` would have turned off.
    """
    res = _result()
    ax = res.plot(kind="snapshot")
    domain = [0.0, 40 * 9.0e-3, 30 * 9.0e-3, 0.0]
    assert [list(image.get_extent()) for image in ax.images] == [
        pytest.approx(domain),
        pytest.approx(domain),
    ]
    assert ax.get_xlim() == pytest.approx((0.0, 0.36))
    assert ax.get_ylim() == pytest.approx((0.27, 0.0))
    assert ax.get_autoscalex_on()
    assert ax.get_autoscaley_on()
    plt.close(ax.figure)

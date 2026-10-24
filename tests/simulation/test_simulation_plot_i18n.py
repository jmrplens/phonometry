#  Copyright (c) 2026. Jose Manuel Requena Plens

"""The simulation (FDTD) ``.plot()`` renderer: its EN/ES labels, and its decimated snapshots."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry.simulation import (
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    elastic_fdtd_simulation,
)
from phonometry.simulation.fdtd import (
    FDTDRecording,
    FDTDRun,
    GaussianPulse,
    fdtd_simulation,
)

if TYPE_CHECKING:
    from matplotlib.image import AxesImage


def _result() -> object:
    mask = np.zeros((30, 40), dtype=bool)
    mask[12:18, 20:22] = True
    return fdtd_simulation(
        FDTDRun(
            c=343.0,
            dx=9.0e-3,
            duration_s=3.0e-3,
            shape=(30, 40),
            sources=[GaussianPulse(ix=7, iy=5, half_width_s=3.0e-4)],
            recording=FDTDRecording(probes=[(10, 5), (24, 10)], snapshot_every=10),
            obstacle_mask=mask,
        )
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
        FDTDRun(
            c=343.0,
            dx=0.01,
            duration_s=1e-3,
            shape=(30, 101),
            sources=[GaussianPulse(ix=50, iy=15, half_width_s=4e-5)],
            recording=FDTDRecording(snapshot_every=10, snapshot_decimation=4),
        )
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
        FDTDRun(
            c=343.0,
            dx=0.01,
            duration_s=1e-3,
            shape=(30, 101),
            sources=[GaussianPulse(ix=50, iy=15, half_width_s=4e-5)],
            obstacle_mask=mask,
            recording=FDTDRecording(snapshot_every=10, snapshot_decimation=4),
        )
    )
    ax = res.plot(kind="snapshot")
    assert ax.images[1].get_extent() == pytest.approx([0.0, 1.01, 0.30, 0.0])
    plt.close(ax.figure)


def test_a_decimated_elastic_snapshot_covers_the_domain_without_stretching() -> None:
    def pulse(t: float) -> float:
        return float(np.exp(-(((t - 2e-5) / 5e-6) ** 2)))

    res = elastic_fdtd_simulation(
        ElasticRun(
            c_p=4000.0,
            c_s=2300.0,
            dx=0.01,
            duration_s=1e-4,
            rho=2500.0,
            shape=(20, 21),
            sources=[ExplosionSource(ix=10, iy=9, waveform=pulse)],
            recording=ElasticRecording(snapshot_every=4, snapshot_decimation=3),
        )
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


def _shown(image: AxesImage) -> tuple[np.ndarray, tuple[float, float], str]:
    """What an image shows: its field, its colour scale and its colormap."""
    vmin, vmax = image.get_clim()
    return np.asarray(image.get_array()), (vmin, vmax), image.get_cmap().name


def test_a_video_frame_shows_the_plot_s_field_scale_and_colormap() -> None:
    """The frame is laid out for a video, but what it shows is the plot's."""
    from matplotlib.figure import Figure

    from phonometry._plot.simulation import fdtd_frame

    res = _result()
    frame = 2
    field = res.snapshots[frame]
    plotted = res.plot(ax=Figure().add_subplot(), kind="snapshot", frame=frame)
    framed = fdtd_frame(
        Figure().add_subplot(),
        field,
        dx=res.dx,
        shape=res.shape,
        sources=res.sources,
        probe_positions=res.probe_positions,
        obstacle_mask=res.obstacle_mask,
        decimation=res.snapshot_decimation,
        color_limit=float(np.abs(field).max()),
        time_s=float(res.snapshot_times[frame]),
        last_time_s=float(res.snapshot_times[-1]),
        language="en",
    )
    shown, scale, colormap = _shown(plotted.images[0])
    assert np.array_equal(np.asarray(framed.get_array()), shown)
    assert framed.get_clim() == scale
    assert framed.get_cmap().name == colormap == "RdBu_r"
    assert framed.get_extent() == pytest.approx(plotted.images[0].get_extent())


def test_an_update_moves_the_data_and_the_time_and_keeps_the_scale() -> None:
    from matplotlib.figure import Figure

    from phonometry._plot.simulation import (
        _update_snapshot,
        fdtd_frame,
        fdtd_snapshot_title,
    )

    res = _result()
    ax = Figure().add_subplot()
    image = fdtd_frame(
        ax,
        res.snapshots[0],
        dx=res.dx,
        shape=res.shape,
        sources=res.sources,
        probe_positions=res.probe_positions,
        obstacle_mask=res.obstacle_mask,
        decimation=1,
        color_limit=0.25,
        time_s=0.0,
        last_time_s=float(res.snapshot_times[-1]),
        language="es",
    )
    later = res.snapshots[-1] * 10.0
    title = fdtd_snapshot_title(float(res.snapshot_times[-1]), "es")
    _update_snapshot(image, later, title)
    assert image.get_clim() == (-0.25, 0.25)
    assert np.array_equal(np.asarray(image.get_array()), later)
    assert ax.get_title() == title
    assert "Campo de presión FDTD" in title
    assert "," in title  # the Spanish decimal comma of the time


def test_an_elastic_video_frame_shows_the_plot_s_field_scale_and_colormap() -> None:
    from matplotlib.figure import Figure

    from phonometry._plot.simulation import elastic_frame

    pulse = GaussianPulse(ix=0, iy=0, half_width_s=4e-5)
    res = elastic_fdtd_simulation(
        ElasticRun(
            c_p=4000.0,
            c_s=2300.0,
            dx=0.01,
            duration_s=2e-3,
            rho=2500.0,
            shape=(24, 30),
            sources=[ExplosionSource(ix=15, iy=12, waveform=pulse.value)],
            recording=ElasticRecording(
                probes=[(5, 5)], snapshot_every=5, snapshot_field="vy"
            ),
        )
    )
    field = res.snapshots[3]
    plotted = res.plot(ax=Figure().add_subplot(), kind="snapshot", frame=3)
    framed = elastic_frame(
        Figure().add_subplot(),
        field,
        dx=res.dx,
        shape=res.shape,
        sources=res.sources,
        probe_positions=res.probe_positions,
        obstacle_mask=res.obstacle_mask,
        decimation=res.snapshot_decimation,
        snapshot_field=res.snapshot_field,
        color_limit=float(np.abs(field).max()),
        time_s=float(res.snapshot_times[3]),
        last_time_s=float(res.snapshot_times[-1]),
        language="es",
    )
    shown, scale, colormap = _shown(plotted.images[0])
    assert np.array_equal(np.asarray(framed.get_array()), shown)
    assert framed.get_clim() == scale
    assert framed.get_cmap().name == colormap == "RdBu_r"
    assert framed.get_extent() == pytest.approx(plotted.images[0].get_extent())


@pytest.mark.parametrize("kind", ["acoustic", "elastic"])
def test_a_decimated_video_frame_shows_the_plot_s_field_over_the_domain(
    kind: str,
) -> None:
    """Each kept sample over its block of cells, the axes ending at the domain's edges, as the plot draws it."""
    from matplotlib.figure import Figure

    from phonometry._plot.simulation import elastic_frame, fdtd_frame

    pulse = GaussianPulse(ix=0, iy=0, half_width_s=4e-5)
    if kind == "acoustic":
        res: Any = fdtd_simulation(
            FDTDRun(
                c=343.0,
                dx=0.01,
                duration_s=1e-3,
                shape=(30, 101),
                sources=[GaussianPulse(ix=50, iy=15, half_width_s=4e-5)],
                recording=FDTDRecording(snapshot_every=10, snapshot_decimation=4),
            )
        )
    else:
        res = elastic_fdtd_simulation(
            ElasticRun(
                c_p=4000.0,
                c_s=2300.0,
                dx=0.01,
                duration_s=2e-4,
                rho=2500.0,
                shape=(20, 21),
                sources=[ExplosionSource(ix=10, iy=9, waveform=pulse.value)],
                recording=ElasticRecording(snapshot_every=4, snapshot_decimation=3),
            )
        )
    frame = 2
    field = res.snapshots[frame]
    plotted = res.plot(ax=Figure().add_subplot(), kind="snapshot", frame=frame)
    where: dict[str, Any] = {
        "dx": res.dx,
        "shape": res.shape,
        "sources": res.sources,
        "probe_positions": res.probe_positions,
        "obstacle_mask": res.obstacle_mask,
        "decimation": res.snapshot_decimation,
        "color_limit": float(np.abs(field).max()),
        "time_s": float(res.snapshot_times[frame]),
        "last_time_s": float(res.snapshot_times[-1]),
        "language": "en",
    }
    ax = Figure().add_subplot()
    if kind == "acoustic":
        framed = fdtd_frame(ax, field, **where)
    else:
        framed = elastic_frame(ax, field, snapshot_field=res.snapshot_field, **where)
    assert res.snapshot_decimation > 1
    assert np.array_equal(np.asarray(framed.get_array()), np.asarray(field))
    assert framed.get_extent() == pytest.approx(plotted.images[0].get_extent())
    assert ax.get_xlim() == pytest.approx(plotted.get_xlim())
    assert ax.get_ylim() == pytest.approx(plotted.get_ylim())
